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

function normalizeLocaleNumber(input: unknown, maxDecimals = 2): { ok: boolean; n?: number } {
  if (input === null || input === undefined) return { ok: false };
  let s = String(input).trim();
  if (!s) return { ok: false };

  // Gruppierungen raus: Space, NBSP, Thin space, schmale Leerzeichen, Apostrophe, etc.
  s = s.replace(/[\s\u00A0\u2000-\u200A\u202F\u205F\u3000'’`´]/g, '');

  const hasComma = s.includes(',');
  const hasDot   = s.includes('.');

  if (hasComma && hasDot) {
    const lastComma = s.lastIndexOf(',');
    const lastDot   = s.lastIndexOf('.');
    const decimalSep = lastComma > lastDot ? ',' : '.';
    if (decimalSep === ',') {
      s = s.replace(/\./g, ''); // Punkte = Gruppierung
      s = s.replace(',', '.');  // Dezimalzeichen -> Punkt
    } else {
      s = s.replace(/,/g, '');  // Komma = Gruppierung
      // Punkt bleibt Dezimal
    }
  } else if (hasComma) {
    s = s.replace(',', '.'); // Dezimal-Komma -> Punkt
  }

  const re = new RegExp(`^[0-9]+(?:\\.[0-9]{1,${maxDecimals}})?$`);
  if (!re.test(s)) return { ok: false };

  const n = Number(s);
  if (!Number.isFinite(n)) return { ok: false };
  return { ok: true, n };
}

export function numberWithLocaleValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const v = control.value;
    if (v === null || v === undefined || String(v).trim() === '') return null;
    const res = normalizeLocaleNumber(v, 2);
    if (!res.ok) return { invalidNumber: { value: v } };
    if ((res.n ?? 0) <= 0) return { nonPositive: { value: v } };
    return null;
  };
}

export function numberWithLocaleValidatorZero(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const v = control.value;
    if (v === null || v === undefined || String(v).trim() === '') return null;
    const res = normalizeLocaleNumber(v, 2);
    if (!res.ok) return { invalidNumber: { value: v } };
    if ((res.n ?? -1) < 0) return { negativeNumber: { value: v } };
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
  