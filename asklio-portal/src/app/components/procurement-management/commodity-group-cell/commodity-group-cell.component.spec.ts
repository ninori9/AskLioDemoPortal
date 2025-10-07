import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CommodityGroupCellComponent } from './commodity-group-cell.component';

describe('CommodityGroupCellComponent', () => {
  let component: CommodityGroupCellComponent;
  let fixture: ComponentFixture<CommodityGroupCellComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CommodityGroupCellComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CommodityGroupCellComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
