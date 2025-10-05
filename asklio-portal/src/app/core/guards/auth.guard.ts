import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../../services/auth/auth.service';
import { decodeJwt } from '../auth/jwt.utils';
import { UserRole } from '../../data/enums/user-role.enum';

export const authGuard: CanActivateFn = (route, state): boolean | UrlTree => {
  const auth = inject(AuthService);
  const router = inject(Router);

  const token = auth.getToken();
  if (!token) {
    return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
  }

  const claims = decodeJwt(token);
  const exp = claims?.exp ? Number(claims.exp) : undefined;
  const isExpired = !!exp && Date.now() / 1000 >= exp;
  if (!claims || isExpired) {
    auth.logout();
    return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
  }

  const requiredRoles = (route.data?.['roles'] as UserRole[] | undefined) ?? [];
  if (requiredRoles.length) {
    const userRoles = auth.snapshot.roles ?? [];
    const allowed = requiredRoles.some(r => userRoles.includes(r));
    if (!allowed) {
      return router.createUrlTree(['/forbidden']);
    }
  }

  return true;
};