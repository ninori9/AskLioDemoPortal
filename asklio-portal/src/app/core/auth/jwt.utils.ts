export type JwtClaims = {
    sub: string;
    username?: string;
    given_name?: string;
    family_name?: string;
    roles?: string[];
    exp?: number;
    iat?: number;
  };
  
  export function decodeJwt(token: string): JwtClaims | null {
    try {
      const [, payload] = token.split('.');
      const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(decodeURIComponent(Array.prototype.map.call(json, (c: string) =>
        '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      ).join('')));
    } catch {
      return null;
    }
  }