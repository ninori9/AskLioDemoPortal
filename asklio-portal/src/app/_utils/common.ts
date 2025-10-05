import { AbstractControl, ValidationErrors, ValidatorFn } from "@angular/forms";
import { format } from "date-fns";
import { MatSnackBarConfig } from '@angular/material/snack-bar';

export function formatEuro(cents: number, opts: Intl.NumberFormatOptions = {}): string {
  const amount = (cents ?? 0) / 100;
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    ...opts,
  }).format(amount);
}
  
export function formatDateString(isoString: string): string {
    if (!isoString) return '';
    const date = new Date(isoString);
    return format(date, "MM/dd/yyyy, hh:mm a"); // e.g. "09/23/2025, 02:30 PM"
}

export function numberWithCommaValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (control.value === null || control.value === undefined || control.value === '') {
      return null; // required handles empty
    }
    const normalized = String(control.value).replace(',', '.');
    const valid = /^[0-9]+(\.[0-9]{1,2})?$/.test(normalized);
    const parsed = parseFloat(normalized);
    const isPositive = !isNaN(parsed) && parsed > 0;

    if (!valid) return { invalidNumber: { value: control.value } };
    if (!isPositive) return { nonPositive: { value: control.value } };
    return null;
  };
}


export function positiveIntegerValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const raw = String(control.value ?? '').trim();
    if (!raw) return { required: true };
    if (!/^\d+$/.test(raw)) return { notInteger: true };
    const n = Number(raw);
    if (!Number.isFinite(n) || n <= 0) return { notPositive: true };
    return null;
  };
}

export function parseLocaleNumber(val: unknown): number {
    if (val === null || val === undefined || val === '') return 0;
    const n = parseFloat(String(val).replace(',', '.'));
    return isFinite(n) ? n : 0;
  }

export const errorSnackBarConfig: MatSnackBarConfig = {
  duration: 5000,
  horizontalPosition: 'end',
  verticalPosition: 'top',
  panelClass: ['error-snackbar'],
};
  