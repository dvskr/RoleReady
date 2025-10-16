import { Mark, mergeAttributes } from "@tiptap/core";

export const Highlight = Mark.create({
  name: "highlight",
  addOptions() {
    return { color: "#fde68a" };
  },
  parseHTML() {
    return [ { tag: "span[data-highlight]" } ];
  },
  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes(HTMLAttributes, { "data-highlight": "true", style: `background-color:${this.options.color}` }), 0];
  },
  addCommands() {
    return {
      setHighlight:
        color => ({ commands }) => {
          return commands.setMark(this.name, { color });
        },
      unsetHighlight:
        () => ({ commands }) => {
          return commands.unsetMark(this.name);
        },
    };
  },
});
