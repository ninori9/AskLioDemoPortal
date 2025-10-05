import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RequestorWorkspaceComponent } from './requestor-workspace.component';

describe('RequestorWorkspaceComponent', () => {
  let component: RequestorWorkspaceComponent;
  let fixture: ComponentFixture<RequestorWorkspaceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RequestorWorkspaceComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RequestorWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
