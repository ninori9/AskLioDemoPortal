import { RequestStatus } from "../enums/request-status.enum";

export interface UpdateProcurementRequestDto {
    version: number;
    status?: RequestStatus;
    commodityGroupID?: number;
}