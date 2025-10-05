import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { errorSnackBarConfig } from '../../_utils/common';

@Injectable({ providedIn: 'root' })
export class ErrorService {
  constructor(private snackBar: MatSnackBar) {}

  handle(error: unknown, message = 'An unexpected error occurred'): void {
    console.error(error);
    this.snackBar.open(message, 'Close', errorSnackBarConfig);
  }
}