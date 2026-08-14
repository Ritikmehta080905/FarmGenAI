import { z } from 'zod';

/**
 * Reusable validation schemas and functions for Enterprise Forms.
 */
export const Validation = {
  password: (password) => {
    const minLength = 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[^A-Za-z0-9]/.test(password);
    
    if (password.length < minLength) return "Password must be at least 8 characters.";
    if (!hasUpper) return "Password must contain an uppercase letter.";
    if (!hasLower) return "Password must contain a lowercase letter.";
    if (!hasNumber) return "Password must contain a number.";
    if (!hasSpecial) return "Password must contain a special character.";
    
    return null;
  },
  email: (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!regex.test(email)) return "Invalid email address format.";
    return null;
  },
  phone: (phone) => {
    const regex = /^[6-9]\d{9}$/;
    if (!regex.test(phone)) return "Must be a valid 10-digit Indian phone number.";
    return null;
  },
  price: (price, minimumSupportPrice = 0) => {
    if (price <= 0) return "Price must be greater than zero.";
    if (price < minimumSupportPrice) return `Price cannot be below MSP (₹${minimumSupportPrice}).`;
    return null;
  },
  quantity: (qty, minVolume = 100) => {
    if (qty < minVolume) return `Minimum trade volume is ${minVolume} kg.`;
    return null;
  }
};

// --- ZOD SCHEMAS ---

const phoneRegex = /^[6-9]\d{9}$/;
const passwordSchema = z.string().min(8, "Password must be at least 8 characters")
  .regex(/[A-Z]/, "Must contain at least one uppercase letter")
  .regex(/[a-z]/, "Must contain at least one lowercase letter")
  .regex(/[0-9]/, "Must contain at least one number")
  .regex(/[^A-Za-z0-9]/, "Must contain at least one special character");

export const registrationSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  phone: z.string().regex(phoneRegex, "Must be a valid 10-digit Indian phone number"),
  password: passwordSchema,
  confirmPassword: z.string(),
  role: z.enum(['farmer', 'buyer', 'warehouse', 'transport']),
  terms: z.literal(true, { errorMap: () => ({ message: "You must accept the terms" }) })
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"]
});

export const listingSchema = z.object({
  crop: z.string().min(1, "Crop name is required"),
  variety: z.string().min(1, "Variety is required"),
  grade: z.enum(['A', 'B', 'C']).default('A'),
  quantity: z.coerce.number().min(1, "Minimum 1 kg required"),
  price: z.coerce.number().min(1, "Price must be greater than 0"),
  moisture: z.coerce.number().min(0).max(100, "Moisture must be between 0-100%").optional().nullable(),
  isOrganic: z.boolean().default(false),
  harvestDate: z.string().min(1, "Harvest date is required"),
  location: z.string().min(1, "Village/Taluka required"),
  transportRequired: z.boolean().default(false),
  warehouseRequired: z.boolean().default(false),
  description: z.string().max(500).optional().nullable(),
});

export const requirementSchema = z.object({
  crop: z.string().min(1, "Crop name is required"),
  quality: z.enum(['A', 'B', 'C', 'ANY']).default('A'),
  quantity: z.coerce.number().min(1, "Minimum 1 kg required"),
  maxBudget: z.coerce.number().min(1, "Budget must be greater than 0"),
  deliveryDate: z.string().min(1, "Delivery date is required"),
  preferredLocation: z.string().optional().nullable(),
  storageRequired: z.boolean().default(false),
  transportRequired: z.boolean().default(true),
});
