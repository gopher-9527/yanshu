package openai_compatible

import (
	"testing"

	"google.golang.org/genai"
)

// TestConvertContentsToMessages_NilContent tests that nil content elements don't cause panic
func TestConvertContentsToMessages_NilContent(t *testing.T) {
	tests := []struct {
		name     string
		contents []*genai.Content
		wantLen  int
		wantErr  bool
	}{
		{
			name:     "nil content element",
			contents: []*genai.Content{nil},
			wantLen:  0,
			wantErr:  false,
		},
		{
			name: "mixed nil and valid content",
			contents: []*genai.Content{
				nil,
				{
					Role: genai.RoleUser,
					Parts: []*genai.Part{
						{Text: "Hello"},
					},
				},
				nil,
				{
					Role: genai.RoleModel,
					Parts: []*genai.Part{
						{Text: "World"},
					},
				},
			},
			wantLen: 2, // Only non-nil contents with text
			wantErr: false,
		},
		{
			name: "all nil contents",
			contents: []*genai.Content{
				nil,
				nil,
				nil,
			},
			wantLen: 0,
			wantErr: false,
		},
		{
			name: "valid content with nil parts",
			contents: []*genai.Content{
				{
					Role: genai.RoleUser,
					Parts: []*genai.Part{
						nil,
						{Text: "Hello"},
						nil,
					},
				},
			},
			wantLen: 1,
			wantErr: false,
		},
		{
			name:     "empty slice",
			contents: []*genai.Content{},
			wantLen:  0,
			wantErr:  false,
		},
		{
			name:     "nil slice",
			contents: nil,
			wantLen:  0,
			wantErr:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// This should not panic
			messages, err := ConvertContentsToMessages(tt.contents)
			
			if (err != nil) != tt.wantErr {
				t.Errorf("ConvertContentsToMessages() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			
			if len(messages) != tt.wantLen {
				t.Errorf("ConvertContentsToMessages() returned %d messages, want %d", len(messages), tt.wantLen)
			}
		})
	}
}

// TestConvertContentsToMessages_ValidContent tests normal operation
func TestConvertContentsToMessages_ValidContent(t *testing.T) {
	contents := []*genai.Content{
		{
			Role: genai.RoleUser,
			Parts: []*genai.Part{
				{Text: "Hello"},
			},
		},
		{
			Role: genai.RoleModel,
			Parts: []*genai.Part{
				{Text: "Hi there!"},
			},
		},
		{
			Role: "system",
			Parts: []*genai.Part{
				{Text: "You are a helpful assistant"},
			},
		},
	}

	messages, err := ConvertContentsToMessages(contents)
	if err != nil {
		t.Fatalf("ConvertContentsToMessages() error = %v", err)
	}

	if len(messages) != 3 {
		t.Errorf("Expected 3 messages, got %d", len(messages))
	}

	// Verify roles
	expectedRoles := []string{"user", "assistant", "system"}
	for i, msg := range messages {
		if role, ok := msg["role"].(string); !ok || role != expectedRoles[i] {
			t.Errorf("Message %d: expected role %s, got %v", i, expectedRoles[i], msg["role"])
		}
	}
}

// TestConvertContentsToMessages_EmptyParts tests content with empty parts
func TestConvertContentsToMessages_EmptyParts(t *testing.T) {
	contents := []*genai.Content{
		{
			Role:  genai.RoleUser,
			Parts: []*genai.Part{}, // Empty parts
		},
		{
			Role: genai.RoleUser,
			Parts: []*genai.Part{
				{Text: ""}, // Empty text
			},
		},
		{
			Role:  genai.RoleUser,
			Parts: nil, // Nil parts
		},
	}

	messages, err := ConvertContentsToMessages(contents)
	if err != nil {
		t.Fatalf("ConvertContentsToMessages() error = %v", err)
	}

	// Should return no messages since all have no valid text
	if len(messages) != 0 {
		t.Errorf("Expected 0 messages, got %d", len(messages))
	}
}
