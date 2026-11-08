import React, { useState } from 'react';
import { ProductBasic } from '../../types/chat';

interface ProductCardBasicProps {
  items: ProductBasic[];
}

export const ProductCardBasic: React.FC<ProductCardBasicProps> = ({ items }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full pt-1" data-purpose="product-basic-list">
      {items.map((product) => (
        <ProductItem key={product.id} product={product} />
      ))}
    </div>
  );
};

const ProductItem: React.FC<{ product: ProductBasic }> = ({ product }) => {
  const [imageError, setImageError] = useState(false);

  return (
    <article
      className="bg-white border border-gray-200 rounded-2xl p-3 shadow-sm flex items-center gap-3 hover:border-gray-300 transition-all"
      data-purpose="product-card-basic"
    >
      {/* Miniatura del producto con fallback seguro */}
      <div className="w-14 h-14 rounded-xl bg-stone-100 flex-shrink-0 overflow-hidden flex items-center justify-center border border-gray-100 relative">
        {product.imageUrl && !imageError ? (
          <img
            src={product.imageUrl}
            alt={product.name}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="w-full h-full bg-red-50 text-[#DC2626] flex items-center justify-center">
            <svg
              className="w-6 h-6 text-[#DC2626]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.75"
                d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Datos básicos */}
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-bold text-gray-900 leading-snug truncate">
          {product.name}
        </h4>
        <p className="text-[11px] text-gray-500 font-medium truncate mt-0.5">
          {product.category}
        </p>

        {/* Badge de Disponibilidad */}
        <div className="mt-1.5">
          {product.available ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Disponible
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-gray-100 text-gray-500 border border-gray-200">
              Agotado
            </span>
          )}
        </div>
      </div>
    </article>
  );
};
