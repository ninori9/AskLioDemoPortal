import { CommonModule } from '@angular/common';
import { Component, ViewChild } from '@angular/core';
import { MatTabChangeEvent, MatTabsModule } from '@angular/material/tabs';
import { RequestorComponent } from '../requestor/requestor.component';
import { MyProcurementRequestsComponent } from '../my-procurement-requests/my-procurement-requests.component';

@Component({
  selector: 'app-requestor-workspace',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    RequestorComponent,
    MyProcurementRequestsComponent,
  ],
  templateUrl: './requestor-workspace.component.html',
  styleUrl: './requestor-workspace.component.scss'
})
export class RequestorWorkspaceComponent {
  @ViewChild(MyProcurementRequestsComponent)
  myRequestsComp?: MyProcurementRequestsComponent;

  onTabChange(evt: MatTabChangeEvent): void {
    if (evt.index === 1) {
      this.myRequestsComp?.refresh();
    }
  }
}
