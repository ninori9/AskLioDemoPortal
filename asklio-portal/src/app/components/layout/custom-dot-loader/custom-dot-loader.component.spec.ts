import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CustomDotLoaderComponent } from './custom-dot-loader.component';

describe('CustomDotLoaderComponent', () => {
  let component: CustomDotLoaderComponent;
  let fixture: ComponentFixture<CustomDotLoaderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CustomDotLoaderComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(CustomDotLoaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
