"""Answers as the providers' own documents show them, for the adapters to be read against.

Each was taken from `docs/research/models/`, which says where it was read and
how. "Copied" is as the provider's page shows it. "Made" was put together
from the provider's reference, which names the fields and gives no sample.
None has met a live service. Two providers' pages were read through a tool
that returns an extraction, so their spacing may differ from the page.
"""
# ruff: noqa: E501
# A copied line is as long as it was on the page.

# Copied. Google's cookbook, quickstarts/rest/Prompting_REST.ipynb. It is
# older than the models that think, so it holds no `thoughtsTokenCount`.
GEMINI_WHOLE = r"""
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "```python\n# Example list to be sorted\nmy_list = [5, 3, 1, 2, 4]\n\n# Sort the list in ascending order using the sort() method\nmy_list.sort()\n\n# Print the sorted list\nprint(my_list)\n```\n\nOutput:\n\n```\n[1, 2, 3, 4, 5]\n```"
          }
        ],
        "role": "model"
      },
      "finishReason": "STOP",
      "index": 0,
      "safetyRatings": [
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "probability": "NEGLIGIBLE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "probability": "NEGLIGIBLE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "probability": "NEGLIGIBLE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "probability": "NEGLIGIBLE"}
      ]
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 9,
    "candidatesTokenCount": 87,
    "totalTokenCount": 96
  }
}
"""

# Made, from Google's reference for `generateContent`.
GEMINI_PROMPT_BLOCKED = r"""
{"promptFeedback": {"blockReason": "SAFETY"},
 "usageMetadata": {"promptTokenCount": 3000, "totalTokenCount": 3000}}
"""

# Made, from the same.
GEMINI_CUT_SHORT = r"""
{"candidates": [{"content": {"parts": [{"text": "{\"status\": \"ok\", \"budget_ops\": ["}],
                             "role": "model"},
                 "finishReason": "MAX_TOKENS", "index": 0}],
 "usageMetadata": {"promptTokenCount": 3000, "candidatesTokenCount": 2048,
                   "totalTokenCount": 5048}}
"""

# Copied. Google's general guide to errors, google.aip.dev/193, and not from
# the Gemini API: no sample of an error from `generateContent` was found. The
# page shortens `details`, which is empty here.
GEMINI_ERROR = r"""
{"error": {"code": 429,
           "message": "The zone 'us-east1-a' does not have enough resources...",
           "status": "RESOURCE_EXHAUSTED",
           "details": []}}
"""

# Copied. developers.openai.com, the reference for creating a response.
OPENAI_WHOLE = r"""
{
  "id": "resp_67ccd2bed1ec8190b14f964abc0542670bb6a6b452d3795b",
  "object": "response",
  "created_at": 1741476542,
  "status": "completed",
  "completed_at": 1741476543,
  "error": null,
  "incomplete_details": null,
  "instructions": null,
  "max_output_tokens": null,
  "model": "gpt-6-astra",
  "output": [
    {
      "type": "message",
      "id": "msg_67ccd2bf17f0819081ff3bb2cf6508e60bb6a6b452d3795b",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "In a peaceful grove beneath a silver moon, a unicorn named Lumina discovered a hidden pool that reflected the stars. As she dipped her horn into the water, the pool began to shimmer, revealing a pathway to a magical realm of endless night skies. Filled with wonder, Lumina whispered a wish for all who dream to find their own hidden magic, and as she glanced back, her hoofprints sparkled like stardust.",
          "annotations": []
        }
      ]
    }
  ],
  "parallel_tool_calls": true,
  "previous_response_id": null,
  "reasoning": {"effort": null, "summary": null},
  "store": true,
  "temperature": 1.0,
  "text": {"format": {"type": "text"}},
  "tool_choice": "auto",
  "tools": [],
  "top_p": 1.0,
  "truncation": "disabled",
  "usage": {
    "input_tokens": 36,
    "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
    "output_tokens": 87,
    "output_tokens_details": {"reasoning_tokens": 0},
    "total_tokens": 123
  },
  "user": null,
  "metadata": {}
}
"""

# Copied, from the guide to structured outputs, and put right: as the page
# prints it there are two stray commas and two lines of comment, and it is
# not JSON. Nothing else was changed.
OPENAI_REFUSAL = r"""
{
  "id": "resp_1234567890",
  "object": "response",
  "created_at": 1721596428,
  "status": "completed",
  "completed_at": 1721596429,
  "error": null,
  "incomplete_details": null,
  "input": [],
  "instructions": null,
  "max_output_tokens": null,
  "model": "gpt-4o-2024-08-06",
  "output": [{
    "id": "msg_1234567890",
    "type": "message",
    "role": "assistant",
    "content": [
      {
        "type": "refusal",
        "refusal": "I'm sorry, I cannot assist with that request."
      }
    ]
  }],
  "usage": {
    "input_tokens": 81,
    "output_tokens": 11,
    "total_tokens": 92,
    "output_tokens_details": {"reasoning_tokens": 0}
  }
}
"""

# Copied, from the guide to reasoning. It holds `cached_tokens` with no
# `cache_write_tokens` beside it.
OPENAI_USAGE_WITH_REASONING = r"""
{"usage": {"input_tokens": 75,
           "input_tokens_details": {"cached_tokens": 0},
           "output_tokens": 1186,
           "output_tokens_details": {"reasoning_tokens": 1024},
           "total_tokens": 1261}}
"""

# Made, from a line the provider's cookbook prints as a Python value.
OPENAI_ERROR = r"""
{"error": {"message": "You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.",
           "type": "insufficient_quota", "param": null, "code": "insufficient_quota"}}
"""

# Copied. api-docs.deepseek.com, the reference for a chat completion.
DEEPSEEK_WHOLE = r"""
{
  "id": "930c60df-bf64-41c9-a88e-3ec75f81e00e",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {"content": "Hello! How can I help you today?", "role": "assistant"},
      "logprobs": null
    }
  ],
  "created": 1705651092,
  "model": "deepseek-flash",
  "object": "chat.completion",
  "system_fingerprint": "fp_7a09fdf9c2",
  "usage": {
    "completion_tokens": 10,
    "prompt_tokens": 16,
    "total_tokens": 26,
    "prompt_tokens_details": {"cached_tokens": 0},
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 16
  }
}
"""

# Copied, from the provider's guide to JSON Output: what `content` held.
DEEPSEEK_JSON_CONTENT = (
    '{"question": "Which is the longest river in the world?", "answer": "The Nile River"}'
)

# Copied. platform.claude.com, working with messages.
ANTHROPIC_WHOLE = r"""
{
  "id": "msg_018gCsTGsXkYJVqYPxTgDHBU",
  "type": "message",
  "role": "assistant",
  "content": [{"type": "text", "text": "Sure, I'd be happy to provide..."}],
  "model": "claude-opus-5-5",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {"input_tokens": 30, "output_tokens": 309}
}
"""

# Copied, from the guide to structured outputs: what the text block held.
ANTHROPIC_JSON_CONTENT = r"""
{
  "name": "John Smith",
  "email": "john@example.com",
  "plan_interest": "Enterprise",
  "demo_requested": true
}
"""

# Copied, from the reference for creating a message: its `usage` and no more.
# The rest of that example is generated and does not hang together.
ANTHROPIC_USAGE_WITH_CACHE = r"""
{
  "cache_creation": {"ephemeral_1h_input_tokens": 0, "ephemeral_5m_input_tokens": 0},
  "cache_creation_input_tokens": 2051,
  "cache_read_input_tokens": 2051,
  "inference_geo": "global",
  "input_tokens": 2095,
  "output_tokens": 503,
  "output_tokens_details": {"thinking_tokens": 0},
  "server_tool_use": {"web_fetch_requests": 2, "web_search_requests": 0},
  "service_tier": "standard"
}
"""

# Copied, from the guide to refusals. The status is 200.
ANTHROPIC_REFUSAL = r"""
{
  "id": "msg_01XFUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "model": "claude-fable-5",
  "content": [],
  "stop_reason": "refusal",
  "stop_details": {
    "type": "refusal",
    "category": "cyber",
    "explanation": "This request was declined because it could enable cyber harm."
  },
  "usage": {"input_tokens": 412, "output_tokens": 0}
}
"""

# Copied, from the page of errors. The status is 404.
ANTHROPIC_NOT_FOUND = r"""
{"type": "error",
 "error": {"type": "not_found_error", "message": "The requested resource could not be found."},
 "request_id": "req_011CSHoEeqs5C35K2UUqR7Fy"}
"""

# Copied, from the page of rate limits. The status is 429.
ANTHROPIC_MONTHLY_CAP = r"""
{"type": "error",
 "error": {"type": "rate_limit_error",
           "message": "You have reached your API usage limits: your organization has crossed its monthly API usage threshold, set based on your organization's API tier. You will regain access on 2026-09-01 at 00:00 UTC.",
           "details": {"error_code": "enforced_spend_limit_reached"}},
 "request_id": "req_018EeWyXxfu5pfWkrYcMdjWG"}
"""

# Copied, from the page on retention. The status is 400, and it is no limit.
ANTHROPIC_RETENTION_NEEDED = r"""
{"type": "error",
 "error": {"type": "invalid_request_error",
           "message": "In order to access this model, your organization or workspace must have data retention enabled."}}
"""

# Made. The provider gives how the message begins and shows no body.
ANTHROPIC_OWN_LIMIT = r"""
{"type": "error",
 "error": {"type": "invalid_request_error",
           "message": "You have reached your specified API usage limits. You will regain access on 2026-10-01 at 00:00 UTC."}}
"""

# Copied, from the guide to streaming, where it is an event in a stream. The
# body of a 529 outside a stream is shown on no page.
ANTHROPIC_OVERLOADED = r"""
{"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}
"""
