/**
 * @typedef {'ACTIVE' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED' | 'INTERVENED'} NegotiationStatus
 */

/**
 * @typedef {Object} OfferData
 * @property {string} id
 * @property {string} agent
 * @property {number} price
 * @property {number} quantity
 * @property {string} quality
 * @property {string} deliveryDate
 * @property {boolean} transportIncluded
 * @property {boolean} warehouseIncluded
 * @property {string} validity
 */

/**
 * @typedef {Object} NegotiationState
 * @property {string} id
 * @property {string} farmer
 * @property {string} buyer
 * @property {string} crop
 * @property {number} quantity
 * @property {NegotiationStatus} status
 * @property {number} min_price
 * @property {number} market_price
 */

export const NEGOTIATION_STATUS = {
  ACTIVE: 'ACTIVE',
  ACCEPTED: 'ACCEPTED',
  REJECTED: 'REJECTED',
  EXPIRED: 'EXPIRED',
  INTERVENED: 'INTERVENED',
};
