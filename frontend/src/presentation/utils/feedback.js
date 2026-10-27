// Notices and successful actions are blue; failures are red in both themes.
export const feedbackClass = (tone) =>
  tone === 'error' ? 'app-notice app-notice--error' : 'app-notice app-notice--info';
