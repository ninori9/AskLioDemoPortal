export interface CreateOrderLineDto {
    description: string;
    unitPriceCents: number;
    quantity: number;
    unit: string;
  }