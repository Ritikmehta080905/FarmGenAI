/**
 * @typedef {'ping' | 'pong' | 'NEW_MESSAGE' | 'OFFER' | 'STATUS_CHANGE' | 'AI_REASONING'} WSEventType
 */

/**
 * @typedef {Object} WSMessage
 * @property {WSEventType} type
 * @property {any} [data]
 * @property {string} [timestamp]
 */

export const WS_EVENTS = {
  PING: 'ping',
  PONG: 'pong',
  NEW_MESSAGE: 'NEW_MESSAGE',
  OFFER: 'OFFER',
  STATUS_CHANGE: 'STATUS_CHANGE',
  AI_REASONING: 'AI_REASONING',
};
