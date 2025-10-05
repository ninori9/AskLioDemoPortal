import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NewProcurementRequestDialogComponent } from './new-procurement-request-dialog.component';

describe('NewProcurementRequestDialogComponent', () => {
  let component: NewProcurementRequestDialogComponent;
  let fixture: ComponentFixture<NewProcurementRequestDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NewProcurementRequestDialogComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NewProcurementRequestDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
