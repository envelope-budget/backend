function payeeData() {
  return {
    renameRules: [],
    addRule() {
      this.renameRules.push({ type: 'matches', text: '' });
    },
    removeRule(index) {
      this.renameRules.splice(index, 1);
    },
  };
}
