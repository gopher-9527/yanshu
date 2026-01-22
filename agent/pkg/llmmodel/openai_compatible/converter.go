package openai_compatible

import (
	"fmt"
	"strings"

	"google.golang.org/genai"
)

// ConvertContentsToMessages converts genai.Content to OpenAI message format
func ConvertContentsToMessages(contents []*genai.Content) ([]map[string]any, error) {
	messages := make([]map[string]any, 0, len(contents))

	for _, content := range contents {
		// Skip nil content to avoid panic
		if content == nil {
			continue
		}

		role := "user"
		if content.Role == genai.RoleModel {
			role = "assistant"
		} else if content.Role == "system" {
			role = "system"
		}

		// Extract text from parts
		var textParts []string
		for _, part := range content.Parts {
			if part != nil && part.Text != "" {
				textParts = append(textParts, part.Text)
			}
		}

		if len(textParts) > 0 {
			messages = append(messages, map[string]any{
				"role":    role,
				"content": strings.Join(textParts, "\n"),
			})
		}
	}

	return messages, nil
}

// ConvertToolsToOpenAIFormat converts ADK tools to OpenAI tool format
// The input is map[string]any as defined in model.LLMRequest
func ConvertToolsToOpenAIFormat(tools map[string]any) ([]map[string]any, error) {
	if len(tools) == 0 {
		return nil, nil
	}

	openAITools := make([]map[string]any, 0, len(tools))

	for name, tool := range tools {
		// Try to handle different tool formats
		openAITool := map[string]any{
			"type": "function",
			"function": map[string]any{
				"name":        name,
				"description": fmt.Sprintf("Tool: %s", name),
			},
		}

		// If tool is a map, extract function information
		if toolMap, ok := tool.(map[string]any); ok {
			// Extract description
			if desc, ok := toolMap["description"].(string); ok {
				openAITool["function"].(map[string]any)["description"] = desc
			}

			// Extract parameters
			if params, ok := toolMap["parameters"]; ok {
				openAITool["function"].(map[string]any)["parameters"] = params
			}
		}

		// If tool is a genai.Tool, handle FunctionDeclarations
		if genaiTool, ok := tool.(*genai.Tool); ok && genaiTool.FunctionDeclarations != nil {
			for _, funcDecl := range genaiTool.FunctionDeclarations {
				if funcDecl == nil {
					continue
				}

				toolEntry := map[string]any{
					"type": "function",
					"function": map[string]any{
						"name":        funcDecl.Name,
						"description": funcDecl.Description,
					},
				}

				// Convert parameters schema if present
				if funcDecl.Parameters != nil {
					params, err := convertSchema(funcDecl.Parameters)
					if err != nil {
						return nil, fmt.Errorf("failed to convert parameters for tool %s: %w", funcDecl.Name, err)
					}
					toolEntry["function"].(map[string]any)["parameters"] = params
				}

				openAITools = append(openAITools, toolEntry)
			}
			continue
		}

		openAITools = append(openAITools, openAITool)
	}

	return openAITools, nil
}

// convertSchema converts genai.Schema to OpenAI parameter schema format
func convertSchema(schema *genai.Schema) (map[string]any, error) {
	if schema == nil {
		return map[string]any{"type": "object", "properties": map[string]any{}}, nil
	}

	result := map[string]any{
		"type": convertType(schema.Type),
	}

	if schema.Description != "" {
		result["description"] = schema.Description
	}

	// Handle object properties
	if schema.Properties != nil && len(schema.Properties) > 0 {
		properties := make(map[string]any)
		for name, prop := range schema.Properties {
			propSchema, err := convertSchema(prop)
			if err != nil {
				return nil, fmt.Errorf("failed to convert property %s: %w", name, err)
			}
			properties[name] = propSchema
		}
		result["properties"] = properties
	}

	// Handle required fields
	if len(schema.Required) > 0 {
		result["required"] = schema.Required
	}

	// Handle array items
	if schema.Items != nil {
		items, err := convertSchema(schema.Items)
		if err != nil {
			return nil, fmt.Errorf("failed to convert array items: %w", err)
		}
		result["items"] = items
	}

	// Handle enum values
	if len(schema.Enum) > 0 {
		result["enum"] = schema.Enum
	}

	return result, nil
}

// convertType converts genai type to OpenAI type string
func convertType(t genai.Type) string {
	switch t {
	case genai.TypeString:
		return "string"
	case genai.TypeNumber:
		return "number"
	case genai.TypeInteger:
		return "integer"
	case genai.TypeBoolean:
		return "boolean"
	case genai.TypeArray:
		return "array"
	case genai.TypeObject:
		return "object"
	default:
		return "string" // Default fallback
	}
}
