export interface User {
  id: string;
  email: string;
  name: string;
  role: 'farmer' | 'buyer' | 'admin' | 'warehouse' | 'transport' | 'processor' | 'compost';
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface CropListing {
  id?: string;
  farmer_id?: string;
  crop: string;
  quantity: number;
  min_price: number;
  location: string;
  quality_grade: string;
  shelf_life_days: number;
  status?: string;
}

export interface NegotiationState {
  status: string;
  final_price?: number;
  scenario_type?: string;
  score?: number;
  quantity?: number;
  logs?: string[];
  explanation?: string;
}

export interface SimulationPayload {
  scenario?: string;
  user_id?: string;
  farmer_name?: string;
  crop?: string;
  quantity?: number;
  min_price?: number;
  location?: string;
  quality?: string;
  language?: string;
}
