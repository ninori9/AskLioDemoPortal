import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ProcurementRequestDialogComponent } from './procurement-request-dialog.component';


describe('ProcurementRequestDialogComponent', () => {
  let component: ProcurementRequestDialogComponent;
  let fixture: ComponentFixture<ProcurementRequestDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProcurementRequestDialogComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProcurementRequestDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
