export interface UserProfile {
  id: string;
  nickname: string;
  avatar: string;        // 이모지
  avatarColor: string;   // 배경색 hex
  dietPreferences: string[];
  allergies: string[];
  createdAt: string;
  updatedAt: string;
}

export interface SavedRecipe {
  id: string;
  title: string;
  time: number;
  difficulty: "쉬움" | "보통" | "어려움";
  servings: number;
  usedIngredients: string[];
  extraIngredients: string[];
  steps: string[];
  thumbnail: string | null;
  savedAt: string;
  rating: number | null;
  memo: string;
  isFavorite: boolean;
  sourceIngredients: string[];
}

export const LS_PROFILE = "fridgeRecipe_profile";
export const LS_RECIPES = "fridgeRecipe_recipes";
