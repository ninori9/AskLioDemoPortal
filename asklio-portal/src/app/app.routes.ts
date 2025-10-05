import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { ProcurementManagementComponent } from './components/procurement-management/procurement-management.component';
import { LoginComponent } from './components/login/login.component';
import { RequestorWorkspaceComponent } from './components/requestor-workspace/requestor-workspace.component';
import { UserRole } from './data/enums/user-role.enum';
import { ForbiddenPageComponent } from './components/forbidden-page/forbidden-page.component';

export const routes: Routes = [
    {
      path: 'login',
      component: LoginComponent,
    },
    {
      path: 'procurement',
      canActivate: [authGuard],
      component: ProcurementManagementComponent,
      data: { roles: [UserRole.Procurement] }
    },
    {
      path: 'requestor',
      canActivate: [authGuard],
      component: RequestorWorkspaceComponent,
    },
    {
      path: 'forbidden',
      component: ForbiddenPageComponent
    },
    {
      path: '',
      redirectTo: 'login',
      pathMatch: 'full'
    },
    {
      path: '**',
      redirectTo: 'login'
    }
];
