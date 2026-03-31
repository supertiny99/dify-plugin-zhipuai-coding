import json
from collections.abc import Generator
from typing import Optional, Union

from dify_plugin.entities.model.llm import (
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
)
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from dify_plugin.errors.model import CredentialsValidateFailedError
from dify_plugin.interfaces.model.large_language_model import LargeLanguageModel
from zai import ZhipuAiClient
from zai.core import StreamResponse
from zai.types.chat import ChatCompletionChunk, Completion, ChoiceDelta

from .._common import _CommonZhipuaiCoding


class ZhipuAICodingLargeLanguageModel(_CommonZhipuaiCoding, LargeLanguageModel):
    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        credentials_kwargs = self._to_credential_kwargs(credentials)
        return self._generate(
            model,
            credentials_kwargs,
            prompt_messages,
            model_parameters,
            tools,
            stop,
            stream,
            user,
        )

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        prompt = self._convert_messages_to_prompt(prompt_messages, tools)
        return self._get_num_tokens_by_gpt2(prompt)

    def validate_credentials(self, model: str, credentials: dict) -> None:
        try:
            credentials_kwargs = self._to_credential_kwargs(credentials)
            self._generate(
                model=model,
                credentials_kwargs=credentials_kwargs,
                prompt_messages=[UserPromptMessage(content="hello")],
                model_parameters={"temperature": 0.5, "thinking": False},
                tools=[],
                stream=False,
            )
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex))

    def _generate(
        self,
        model: str,
        credentials_kwargs: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        extra_model_kwargs = {}
        if stop:
            extra_model_kwargs["stop"] = stop

        client = ZhipuAiClient(
            api_key=credentials_kwargs["api_key"],
            base_url=credentials_kwargs.get("base_url"),
        )

        if len(prompt_messages) == 0:
            raise ValueError("At least one message is required")

        if prompt_messages[0].role == PromptMessageRole.SYSTEM:
            if not prompt_messages[0].content:
                prompt_messages = prompt_messages[1:]

        # Build deduplicated message list
        new_prompt_messages: list[PromptMessage] = []
        for prompt_message in prompt_messages:
            copy_prompt_message = prompt_message.model_copy()
            if copy_prompt_message.role in {
                PromptMessageRole.USER,
                PromptMessageRole.SYSTEM,
                PromptMessageRole.TOOL,
            }:
                if isinstance(copy_prompt_message.content, list):
                    continue
                if not isinstance(copy_prompt_message.content, str):
                    continue
                if (
                    new_prompt_messages
                    and new_prompt_messages[-1].role == PromptMessageRole.USER
                    and copy_prompt_message.role == PromptMessageRole.USER
                ):
                    new_prompt_messages[-1].content += "\n\n" + copy_prompt_message.content
                elif copy_prompt_message.role in {
                    PromptMessageRole.USER,
                    PromptMessageRole.TOOL,
                }:
                    new_prompt_messages.append(copy_prompt_message)
                elif copy_prompt_message.role == PromptMessageRole.SYSTEM:
                    new_prompt_message = SystemPromptMessage(content=copy_prompt_message.content)
                    new_prompt_messages.append(new_prompt_message)
                else:
                    new_prompt_message = UserPromptMessage(content=copy_prompt_message.content)
                    new_prompt_messages.append(new_prompt_message)
            elif (
                new_prompt_messages
                and new_prompt_messages[-1].role == PromptMessageRole.ASSISTANT
            ):
                new_prompt_messages[-1].content += "\n\n" + copy_prompt_message.content
            else:
                new_prompt_messages.append(copy_prompt_message)

        # Handle response_format
        if "response_format" in model_parameters:
            response_format = model_parameters.get("response_format")
            if response_format == "json_schema":
                json_schema = model_parameters.get("json_schema")
                if not json_schema:
                    raise ValueError("Must define JSON Schema when the response format is json_schema")
                try:
                    schema = json.loads(json_schema)
                except Exception:
                    raise ValueError(f"not correct json_schema format: {json_schema}")
                model_parameters.pop("json_schema")
                model_parameters["response_format"] = {
                    "type": "json_schema",
                    "json_schema": schema,
                }
            else:
                model_parameters["response_format"] = {"type": response_format}
        elif "json_schema" in model_parameters:
            del model_parameters["json_schema"]

        # Handle thinking mode
        if "thinking" in model_parameters:
            thinking = model_parameters.pop("thinking")
            if thinking:
                model_parameters["thinking"] = {"type": "enabled"}
            else:
                model_parameters["thinking"] = {"type": "disabled"}

        if "stream_options" in model_parameters:
            del model_parameters["stream_options"]

        # Build params
        params = {"model": model, "messages": [], **model_parameters}
        for prompt_message in new_prompt_messages:
            if prompt_message.role == PromptMessageRole.TOOL:
                params["messages"].append(
                    {
                        "role": "tool",
                        "content": prompt_message.content,
                        "tool_call_id": prompt_message.tool_call_id,
                    }
                )
            elif isinstance(prompt_message, AssistantPromptMessage):
                if prompt_message.tool_calls:
                    params["messages"].append(
                        {
                            "role": "assistant",
                            "content": prompt_message.content,
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": tool_call.type,
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments,
                                    },
                                }
                                for tool_call in prompt_message.tool_calls
                            ],
                        }
                    )
                else:
                    params["messages"].append(
                        {"role": "assistant", "content": prompt_message.content}
                    )
            else:
                params["messages"].append(
                    {
                        "role": prompt_message.role.value,
                        "content": prompt_message.content,
                    }
                )

        if tools and len(tools) > 0:
            params["tools"] = [
                {"type": "function", "function": tool.model_dump()} for tool in tools
            ]

        if stream:
            response = client.chat.completions.create(
                stream=stream, **params, **extra_model_kwargs
            )
            return self._handle_generate_stream_response(
                model, credentials_kwargs, tools, response, prompt_messages
            )

        response = client.chat.completions.create(**params, **extra_model_kwargs)
        return self._handle_generate_response(
            model, credentials_kwargs, tools, response, prompt_messages
        )

    def _handle_generate_response(
        self,
        model: str,
        credentials: dict,
        tools: Optional[list[PromptMessageTool]],
        response: Completion,
        prompt_messages: list[PromptMessage],
    ) -> LLMResult:
        text = ""
        assistant_tool_calls: list[AssistantPromptMessage.ToolCall] = []
        for choice in response.choices:
            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    if tool_call.type == "function":
                        assistant_tool_calls.append(
                            AssistantPromptMessage.ToolCall(
                                id=tool_call.id,
                                type=tool_call.type,
                                function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                                    name=tool_call.function.name,
                                    arguments=tool_call.function.arguments,
                                ),
                            )
                        )
            if choice.message.reasoning_content:
                text += "<think>\n" + choice.message.reasoning_content + "\n</think>"
            text += choice.message.content or ""

        prompt_usage = response.usage.prompt_tokens
        completion_usage = response.usage.completion_tokens
        usage = self._calc_response_usage(model, credentials, prompt_usage, completion_usage)
        result = LLMResult(
            model=model,
            prompt_messages=prompt_messages,
            message=AssistantPromptMessage(content=text, tool_calls=assistant_tool_calls),
            usage=usage,
        )
        return result

    def _handle_generate_stream_response(
        self,
        model: str,
        credentials: dict,
        tools: Optional[list[PromptMessageTool]],
        responses: StreamResponse[ChatCompletionChunk],
        prompt_messages: list[PromptMessage],
    ) -> Generator:
        is_reasoning = False
        full_assistant_content = ""
        for chunk in responses:
            if len(chunk.choices) == 0:
                continue
            delta = chunk.choices[0]
            if (
                delta.finish_reason is None
                and (delta.delta.content is None or delta.delta.content == "")
                and (delta.delta.reasoning_content is None or delta.delta.reasoning_content == "")
                and delta.delta.tool_calls is None
            ):
                continue

            assistant_tool_calls: list[AssistantPromptMessage.ToolCall] = []
            for tool_call in delta.delta.tool_calls or []:
                if tool_call.type == "function":
                    assistant_tool_calls.append(
                        AssistantPromptMessage.ToolCall(
                            id=tool_call.id,
                            type=tool_call.type,
                            function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                                name=tool_call.function.name,
                                arguments=tool_call.function.arguments,
                            ),
                        )
                    )

            resp_content, is_reasoning = self._wrap_thinking_by_reasoning_content(
                delta.delta, is_reasoning
            )
            assistant_prompt_message = AssistantPromptMessage(
                content=resp_content, tool_calls=assistant_tool_calls
            )
            full_assistant_content += resp_content

            if delta.finish_reason is not None and chunk.usage is not None:
                completion_tokens = chunk.usage.completion_tokens
                prompt_tokens = chunk.usage.prompt_tokens
                usage = self._calc_response_usage(
                    model, credentials, prompt_tokens, completion_tokens
                )
                yield LLMResultChunk(
                    model=chunk.model,
                    prompt_messages=prompt_messages,
                    system_fingerprint="",
                    delta=LLMResultChunkDelta(
                        index=delta.index,
                        message=assistant_prompt_message,
                        finish_reason=delta.finish_reason,
                        usage=usage,
                    ),
                )
            else:
                yield LLMResultChunk(
                    model=chunk.model,
                    prompt_messages=prompt_messages,
                    system_fingerprint="",
                    delta=LLMResultChunkDelta(
                        index=delta.index,
                        message=assistant_prompt_message,
                        finish_reason=delta.finish_reason,
                    ),
                )

    def _convert_one_message_to_text(self, message: PromptMessage) -> str:
        human_prompt = "\n\nHuman:"
        ai_prompt = "\n\nAssistant:"
        content = message.content
        if isinstance(message, UserPromptMessage):
            message_text = f"{human_prompt} {content}"
        elif isinstance(message, AssistantPromptMessage):
            message_text = f"{ai_prompt} {content}"
        elif isinstance(message, SystemPromptMessage | ToolPromptMessage):
            message_text = content
        else:
            raise ValueError(f"Got unknown type {message}")
        return message_text

    def _convert_messages_to_prompt(
        self,
        messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> str:
        messages = messages.copy()
        text = "".join(
            (self._convert_one_message_to_text(message) for message in messages)
        )
        if tools and len(tools) > 0:
            text += "\n\nTools:"
            for tool in tools:
                text += f"\n{tool.model_dump_json()}"
        return text.rstrip()

    def _wrap_thinking_by_reasoning_content(
        self, delta: ChoiceDelta, is_reasoning: bool
    ) -> tuple[str, bool]:
        content = delta.content or ""
        reasoning_content = delta.reasoning_content
        if reasoning_content:
            if not is_reasoning:
                content = "<think>\n" + reasoning_content
                is_reasoning = True
            else:
                content = reasoning_content
        elif is_reasoning and content:
            content = "\n</think>" + content
            is_reasoning = False
        return content, is_reasoning
