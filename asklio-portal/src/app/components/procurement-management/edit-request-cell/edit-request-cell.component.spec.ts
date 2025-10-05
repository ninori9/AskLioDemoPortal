import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EditRequestCellComponent } from './edit-request-cell.component';

describe('EditRequestCellComponent', () => {
  let component: EditRequestCellComponent;
  let fixture: ComponentFixture<EditRequestCellComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EditRequestCellComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EditRequestCellComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
