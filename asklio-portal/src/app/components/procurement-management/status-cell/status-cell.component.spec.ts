import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StatusCellComponent } from './status-cell.component';

describe('StatusCellComponent', () => {
  let component: StatusCellComponent;
  let fixture: ComponentFixture<StatusCellComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatusCellComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StatusCellComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
