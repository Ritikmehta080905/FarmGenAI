/**
 * @typedef {'farmer' | 'buyer' | 'warehouse' | 'transport' | 'processor' | 'admin'} UserRole
 */

/**
 * @typedef {Object} UserProfile
 * @property {string} id
 * @property {string} name
 * @property {string} email
 * @property {UserRole} role
 * @property {string} [phone]
 * @property {string} [location]
 * @property {number} [trustScore]
 */

export const USER_ROLES = {
  FARMER: 'farmer',
  BUYER: 'buyer',
  WAREHOUSE: 'warehouse',
  TRANSPORT: 'transport',
  PROCESSOR: 'processor',
  ADMIN: 'admin',
};
