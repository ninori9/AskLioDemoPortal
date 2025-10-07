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

export function numberWithCommaValidatorZero(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value;
    if (value === null || value === undefined || value === '') {
      return null; // don't block empty fields
    }

    const normalized = String(value).replace(',', '.').trim();
    if (!/^[0-9]+(\.[0-9]{1,2})?$/.test(normalized)) {
      return { invalidNumber: { value } };
    }

    const parsed = parseFloat(normalized);
    if (isNaN(parsed) || parsed < 0) {
      return { negativeNumber: { value } };
    }

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
  if (val === null || val === undefined) return 0;
  let s = String(val).trim();
  if (!s) return 0;

  const hasComma = s.includes(',');
  const hasDot   = s.includes('.');

  if (hasComma && hasDot) {
    const lastComma = s.lastIndexOf(',');
    const lastDot   = s.lastIndexOf('.');
    const decimalSep = lastComma > lastDot ? ',' : '.';

    if (decimalSep === ',') {
      s = s.replace(/\./g, '');  // remove all dots (grouping)
      s = s.replace(',', '.');   // decimal to dot
    } else {
      s = s.replace(/,/g, '');   // remove all commas (grouping)
    }
  } else if (hasComma) {
    s = s.replace(',', '.');
  }

  const n = Number(s);
  return Number.isFinite(n) ? n : 0;
}

export const errorSnackBarConfig: MatSnackBarConfig = {
  duration: 5000,
  horizontalPosition: 'end',
  verticalPosition: 'top',
  panelClass: ['error-snackbar'],
};
  