import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-forbidden-page',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    <div class="forbidden-wrap">
      <div class="panel">
        <mat-icon class="lock-icon" fontSet="material-symbols-rounded">lock</mat-icon>
        <h1 class="title">Access Denied</h1>
        <p class="subtitle">
          You do not have the necessary permissions to view this page.
        </p>

        <div class="actions">
          <button mat-stroked-button (click)="goBack()">
            <mat-icon>arrow_back</mat-icon>
            <span>Go Back</span>
          </button>
          <button mat-flat-button color="primary" (click)="goHome()">
            <mat-icon>home</mat-icon>
            <span>Home</span>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .forbidden-wrap {
      min-height: calc(100vh - 64px); /* leave room if you have a top bar */
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: var(--color-content-bg, #121212);
    }

    .panel {
      width: 100%;
      max-width: 560px;
      padding: 28px 24px;
      background: var(--color-surface, #1e1e1e);
      border: 1px solid color-mix(in oklab, var(--border-color, #2a2a2a), #000 10%);
      border-radius: 14px;
      box-shadow: var(--shadow-1, 0 10px 30px rgba(0,0,0,.35));
      text-align: center;
    }

    .lock-icon {
      font-size: 48px;
      height: 48px;
      width: 48px;
      color: var(--color-warn, #e53935);
      margin-bottom: 8px;
    }

    .title {
      margin: 0 0 6px;
      font-weight: 800;
      font-size: 1.6rem;
      color: var(--text-on-surface, #fff);
      letter-spacing: -0.2px;
    }

    .subtitle {
      margin: 0 0 18px;
      color: color-mix(in oklab, var(--text-on-surface, #fff), transparent 30%);
    }

    .actions {
      display: flex;
      gap: 10px;
      justify-content: center;
      margin-top: 8px;
    }

    .actions button mat-icon {
      margin-right: 6px;
    }
  `]
})
export class ForbiddenPageComponent {
  constructor(private router: Router) {}

  goBack(): void {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      this.router.navigate(['/']);
    }
  }

  goHome(): void {
    this.router.navigate(['/']);
  }
}