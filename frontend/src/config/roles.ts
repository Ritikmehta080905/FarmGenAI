/**
 * Enterprise Application Roles
 */

export const ROLES = {
  FARMER: 'farmer',
  BUYER: 'buyer',
  WAREHOUSE: 'warehouse',
  TRANSPORT: 'transport',
  PROCESSOR: 'processor',
  ADMIN: 'admin'
};

export const ROLE_LABELS = {
  [ROLES.FARMER]: 'Farmer',
  [ROLES.BUYER]: 'Buyer',
  [ROLES.WAREHOUSE]: 'Warehouse Provider',
  [ROLES.TRANSPORT]: 'Logistics & Transport',
  [ROLES.PROCESSOR]: 'Processor',
  [ROLES.ADMIN]: 'Administrator'
};

export const DEFAULT_REDIRECTS = {
  [ROLES.FARMER]: '/dashboard/farmer',
  [ROLES.BUYER]: '/dashboard/buyer',
  [ROLES.WAREHOUSE]: '/dashboard/warehouse',
  [ROLES.TRANSPORT]: '/dashboard/transport',
  [ROLES.PROCESSOR]: '/dashboard/processor',
  [ROLES.ADMIN]: '/dashboard/admin'
};
