import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MobilePaginatorComponent } from './mobile-paginator.component';

describe('MobilePaginatorComponent', () => {
  let component: MobilePaginatorComponent;
  let fixture: ComponentFixture<MobilePaginatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MobilePaginatorComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(MobilePaginatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
