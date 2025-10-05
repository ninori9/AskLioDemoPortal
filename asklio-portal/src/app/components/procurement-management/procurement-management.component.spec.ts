import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProcurementManagementComponent } from './procurement-management.component';

describe('ProcurementManagementComponent', () => {
  let component: ProcurementManagementComponent;
  let fixture: ComponentFixture<ProcurementManagementComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProcurementManagementComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProcurementManagementComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
