import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { UserRole } from '../../data/enums/user-role.enum';
import { CustomDotLoaderComponent } from '../layout/custom-dot-loader/custom-dot-loader.component';
import { finalize } from 'rxjs';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatInputModule,
    FormsModule,
    ReactiveFormsModule,
    MatIconModule,
    CustomDotLoaderComponent
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  private formBuilder = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  hidePassword = true;
  loggingIn = false;
  loginFailed = false;

  loginForm = this.formBuilder.group({
    emailUserName: ['', [Validators.required, Validators.minLength(4)]],
    password: ['', [Validators.required, Validators.minLength(4)]],
  });

  get loginButtonDisabled(): boolean {
    return this.loggingIn || this.loginForm.invalid;
  }

  onLoginSubmit(): void {
    if (this.loginForm.invalid) return;
  
    this.loggingIn = true;
    this.loginFailed = false;
  
    const { emailUserName, password } = this.loginForm.value;
    if (!emailUserName || !password) return;
  
    this.authService
      .login(emailUserName.trim(), password.trim())
      .pipe(finalize(() => (this.loggingIn = false)))
      .subscribe({
        next: () => {
          const roles = this.authService.snapshot.roles ?? [];
          const target = roles.includes(UserRole.Procurement) ? '/procurement' : '/requestor';
          this.router.navigate([target]);
        },
        error: () => {
          this.loginFailed = true;
        },
      });
  }
}
