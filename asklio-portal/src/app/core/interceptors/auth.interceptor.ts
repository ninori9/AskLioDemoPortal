import { HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";
import { AuthService } from "../../services/auth/auth.service";
import { environment } from "../../../environments/environment";

export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const token = inject(AuthService).getToken();
    const headers: Record<string, string> = { 'X-Client-Key': environment.clientSharedApiKey };
  
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  
    return next(req.clone({ setHeaders: headers }));
  };