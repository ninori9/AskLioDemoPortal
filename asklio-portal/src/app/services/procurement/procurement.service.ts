import { inject, Injectable } from '@angular/core';
import { RequestStatus } from '../../data/enums/request-status.enum';
import { delay, map, Observable, of } from 'rxjs';
import { ProcurementRequestLiteDto } from '../../data/dtos/procurement-request-lite.dto';
import { COMMODITY_GROUPS, MOCK_PROCUREMENT_REQUESTS, PROCUREMENT_REQUEST } from '../../_utils/generate-mock-data';
import { CommodityGroupDto } from '../../data/dtos/commodity-group.dto';
import { ProcurementRequestDto } from '../../data/dtos/procurement-request.dto';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { CreateProcurementRequestDto } from '../../data/dtos/create-procurement-request.dto';
import { UpdateProcurementRequestDto } from '../../data/dtos/update-procurement-request.dto';

@Injectable({
  providedIn: 'root'
})
export class ProcurementService {
  private http = inject(HttpClient);

  /**
   * Get procurement requests.
   * @param status Optional status filter (Open | InProgress | Closed)
   */
  getRequests(status?: RequestStatus): Observable<ProcurementRequestLiteDto[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    return this.http.get<ProcurementRequestLiteDto[]>(`${environment.apiUrl}/procurement`, { params });
  }

  /**
   * Get the user's procurement requests.
   * @param status Optional status filter (Open | InProgress | Closed)
   */
  getMyRequests(status?: RequestStatus): Observable<ProcurementRequestLiteDto[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    return this.http.get<ProcurementRequestLiteDto[]>(
      `${environment.apiUrl}/procurement/mine`,
      { params }
    );
  }

  /**
   * Get all available commodity groups
   */
  getCommodityGroups(): Observable<Array<CommodityGroupDto>> {
    return this.http.get<Array<CommodityGroupDto>>(`${environment.apiUrl}/commodity-groups/all`);
  }

  /**
   * Create a new procurement request
   */
  createRequest(request: CreateProcurementRequestDto): Observable<ProcurementRequestLiteDto> {
    return this.http.post<ProcurementRequestLiteDto>(
      `${environment.apiUrl}/procurement`,
      request
    );
  }

  /**
   * Get procurement request details
   */
  getRequestByID(id: string): Observable<ProcurementRequestDto> {
    return this.http.get<ProcurementRequestDto>(`${environment.apiUrl}/procurement/${id}`);
  }

  /**
   * Update request status or commodity group
   */
  updateRequest(id: string, body: UpdateProcurementRequestDto): Observable<ProcurementRequestDto> {
    return this.http.patch<ProcurementRequestDto>(`${environment.apiUrl}/procurement/${id}`, body);
  }
}
