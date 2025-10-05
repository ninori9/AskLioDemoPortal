import { Component, inject, Input } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { NgIf } from '@angular/common';
import { AvatarComponent } from '../avatar/avatar.component';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../../services/auth/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-nav-bar',
  standalone: true,
  imports: [
    NgIf,
    MatToolbarModule,
    MatIconModule,
    AvatarComponent,
    MatButtonModule
  ],
  templateUrl: './nav-bar.component.html',
  styleUrl: './nav-bar.component.scss'
})
export class NavBarComponent {
  @Input() loggedIn: boolean = false;

  private authService = inject(AuthService);

  private sub?: Subscription;

  public initials = 'LO';

  ngOnInit(): void {
    this.initials = this.computeInitials();

    this.sub = this.authService.loggedIn$.subscribe(() => {
      this.initials = this.computeInitials();
    });
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  onLogoutClick(): void {
    this.authService.logout();
  }

  private computeInitials(): string {
    const s = this.authService.snapshot;

    const first = (s.givenName ?? '').trim();
    const last = (s.familyName ?? '').trim();
    const username = (s.username ?? '').trim();

    const firstInitial = first ? first[0] : '';
    const lastInitial = last ? last[0] : '';

    const byName = (firstInitial + lastInitial).toUpperCase();
    if (byName.length === 2) return byName;

    if (username) return username.slice(0, 2).toUpperCase();

    return 'LO';
  }
}
