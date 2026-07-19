import { showLegalNotice } from '../../utils/legalNotice.js'

function strokeIcon(paths) {
  return `<svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`
}

export const authIcons = {
  user: strokeIcon('<path d="M5 20c1.4-3.7 4.3-5.6 7-5.6s5.6 1.9 7 5.6"/><circle cx="12" cy="8" r="3.5"/>'),
  lock: strokeIcon('<rect x="5.2" y="10.2" width="13.6" height="9.8" rx="2.3"/><path d="M8.4 10.2V7.9a3.6 3.6 0 1 1 7.2 0v2.3"/>'),
  eye: strokeIcon('<path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6Z"/><circle cx="12" cy="12" r="2.8"/>'),
  eyeOff: strokeIcon('<path d="m4 4 16 16"/><path d="M10.6 6.4c.5-.1.9-.2 1.4-.2 6.4 0 10 5.8 10 5.8a17 17 0 0 1-3.2 3.8"/><path d="M6.5 7.3C4 9 2 12 2 12s3.6 6 10 6c1.7 0 3.2-.4 4.6-1"/>'),
}

export function openLegalDoc(title) {
  showLegalNotice(title)
}
