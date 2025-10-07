import { RequestStatus } from "../enums/request-status.enum";
import { CommodityGroupDto } from "./commodity-group.dto";

export interface ProcurementRequestLiteDto {
    id: string;
    title: string;
    commodityGroup: CommodityGroupDto;
    commodityGroupConfidence?: number;
    vendorName: string;
    totalCostsCent: number;
    requestorName: string;
    requestorDepartment: string;
    status: RequestStatus;
    createdAt: string;
}