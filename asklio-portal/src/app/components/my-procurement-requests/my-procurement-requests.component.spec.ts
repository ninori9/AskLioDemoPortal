import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MyProcurementRequestsComponent } from './my-procurement-requests.component';

describe('MyProcurementRequestsComponent', () => {
  let component: MyProcurementRequestsComponent;
  let fixture: ComponentFixture<MyProcurementRequestsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MyProcurementRequestsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MyProcurementRequestsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
