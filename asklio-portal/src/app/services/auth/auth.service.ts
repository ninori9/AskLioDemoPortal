import { inject, Injectable } from '@angular/core';
import { BehaviorSubject, delay, map, Observable, of, tap } from 'rxjs';
import { Router } from '@angular/router';
import { UserRole } from '../../data/enums/user-role.enum';
import { HttpClient } from '@angular/common/http';
import { AuthState } from '../../data/models/auth-state.model';
import { decodeJwt, JwtClaims } from '../../core/auth/jwt.utils';
import { LoginRequestDto } from '../../data/dtos/login-request.dto';
import { TokenResponse } from '../../data/dtos/token-response.dto';
import { environment } from '../../../environments/environment';

const STORAGE_TOKEN = 'auth.token';
const STORAGE_CLAIMS = 'auth.claims';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private state$ = new BehaviorSubject<AuthState>({ loggedIn: false });

  readonly loggedIn$ = this.state$.pipe(map(s => s.loggedIn));
  readonly roles$ = this.state$.pipe(map(s => s.roles ?? []));

  get snapshot() { return this.state$.value; }

  constructor() {
    // Rehydrate from sessionStorage
    const token = sessionStorage.getItem(STORAGE_TOKEN) || undefined;
    const claimsRaw = sessionStorage.getItem(STORAGE_CLAIMS);
    const claims: JwtClaims | undefined = claimsRaw ? JSON.parse(claimsRaw) : undefined;

    if (token && claims) {
      this.state$.next(this.buildState(token, claims));
    }
  }

  login(username: string, password: string) {
    const body: LoginRequestDto = { username: username.trim(), password: password.trim() };
    return this.http.post<TokenResponse>(`${environment.apiUrl}/auth/login`, body).pipe(
      tap(res => {
        const token = res.access_token;
        const claims = decodeJwt(token);
        if (!claims) throw new Error('Invalid token');

        // Persist for the session
        sessionStorage.setItem(STORAGE_TOKEN, token);
        sessionStorage.setItem(STORAGE_CLAIMS, JSON.stringify(claims));

        this.state$.next(this.buildState(token, claims));
      })
    );
  }

  logout(): void {
    sessionStorage.removeItem(STORAGE_TOKEN);
    sessionStorage.removeItem(STORAGE_CLAIMS);
    this.state$.next({ loggedIn: false });
    this.router.navigate(['/logout']);
  }

  getToken(): string | undefined {
    return this.state$.value.token;
  }

  private buildState(token: string, claims: JwtClaims): AuthState {
    const mappedRoles = (claims.roles ?? []).map(r => this.toRoleEnum(r)).filter(Boolean) as UserRole[];
    return {
      loggedIn: true,
      token,
      roles: mappedRoles,
      givenName: claims.given_name,
      familyName: claims.family_name,
      userId: claims.sub,
      username: claims.username,
    };
  }

  private toRoleEnum(r: string): UserRole | undefined {
    // Map backend strings to your enum
    switch (r) {
      case 'Manager': return UserRole.Procurement as UserRole;
      case 'Requestor': return UserRole.Requestor as UserRole;
      default: return undefined;
    }
  }
}
