/**
 * @typedef {Object} ApiResponse
 * @property {boolean} success
 * @property {any} [data]
 * @property {string} [message]
 * @property {string} [detail]
 */

/**
 * @typedef {Object} PaginatedResponse
 * @property {Array<any>} items
 * @property {number} total
 * @property {number} page
 * @property {number} pageSize
 */

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
};
