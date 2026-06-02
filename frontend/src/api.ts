import axios from 'axios';

const API_URL = '/api';

export interface UserPreferences { category: string; flexibility: boolean; dietary?: string; }
export interface UserInput { origin: string; destination: string; start_date: string; end_date: string; budget: number; preferences: UserPreferences; }

export const planTrip = async (input: UserInput) => (await axios.post(`${API_URL}/plan-trip`, input)).data;
export const updatePlan = async (planId: string, reason: string) => (await axios.post(`${API_URL}/update-plan/${planId}?reason=${encodeURIComponent(reason)}`)).data;
export const getTrending = async () => (await axios.get(`${API_URL}/trending-destinations`)).data;
export const getOffers = async () => (await axios.get(`${API_URL}/offers`)).data;
export const searchTransport = async (origin: string, destination: string, type: string) => (await axios.get(`${API_URL}/search-transport?origin=${origin}&destination=${destination}&type=${type}`)).data;
export const searchHotels = async (destination: string) => (await axios.get(`${API_URL}/search-hotels?destination=${destination}`)).data;
export const getMyTrips = async () => (await axios.get(`${API_URL}/my-trips`)).data;
