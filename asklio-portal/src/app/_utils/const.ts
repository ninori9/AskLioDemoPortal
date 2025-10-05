import { RequestStatus } from "../data/enums/request-status.enum";

/**
 * Human-readable labels for display purposes.
 * Always use these for UI instead of the raw enum values.
 */
export const REQUEST_STATUS_LABELS: Record<RequestStatus, string> = {
    [RequestStatus.All]: 'All',
    [RequestStatus.Open]: 'Open',
    [RequestStatus.InProgress]: 'In Progress',
    [RequestStatus.Closed]: 'Closed',
  };