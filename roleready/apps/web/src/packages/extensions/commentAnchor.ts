import { Mark, mergeAttributes } from "@tiptap/core";

export const CommentAnchor = Mark.create({
  name: "commentAnchor",
  
  addAttributes() {
    return {
      id: {
        default: null,
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-comment]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-comment': '1',
        class: 'bg-yellow-100 border-b-2 border-yellow-300 cursor-pointer',
        title: 'Click to view comment',
      }),
      0,
    ];
  },

  addCommands() {
    return {
      setCommentAnchor: (attributes) => ({ commands }) => {
        return commands.setMark(this.name, attributes);
      },
      toggleCommentAnchor: (attributes) => ({ commands }) => {
        return commands.toggleMark(this.name, attributes);
      },
      unsetCommentAnchor: () => ({ commands }) => {
        return commands.unsetMark(this.name);
      },
    };
  },
});
