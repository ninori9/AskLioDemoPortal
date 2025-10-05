import { UserRole } from "../enums/user-role.enum";

export interface AuthState {
    loggedIn: boolean;
    token?: string;
    roles?: UserRole[];
    givenName?: string;
    familyName?: string;
    userId?: string;
    username?: string;
  };
  