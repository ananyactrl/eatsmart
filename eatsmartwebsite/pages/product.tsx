import Head from 'next/head'
import { useState, useEffect } from 'react'
import ProductCard from '../components/ProductCard'
import styles from '../styles/ProductsPage.module.css'

type ProductItem = {
    id: string
    barcode?: string
    product_name: string
    brand?: string
    manufacturer?: string
    region?: string
    weight?: string
    fssai_license?: string
    image_url?: string
    is_verified?: boolean
    created_at?: string
}

type ProductsResponse = {
    products: ProductItem[]
    total: number
    regions: string[]
    brands: string[]
}

export default function Product() {
    const [query, setQuery] = useState('')
    const [products, setProducts] = useState<ProductItem[]>([])
    const [filteredProducts, setFilteredProducts] = useState<ProductItem[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedRegion, setSelectedRegion] = useState<string>('')
    const [selectedBrand, setSelectedBrand] = useState<string>('')
    const [regions, setRegions] = useState<string[]>([])
    const [brands, setBrands] = useState<string[]>([])
    const [total, setTotal] = useState(0)

    useEffect(() => {
        fetchProducts()
    }, [])

    useEffect(() => {
        // Filter products by search query
        if (!query.trim() && !selectedRegion && !selectedBrand) {
            setFilteredProducts(products)
        } else {
            let filtered = [...products]

            // Apply search query filter
            if (query.trim()) {
                const lowerQuery = query.toLowerCase()
                filtered = filtered.filter(p =>
                    p.product_name?.toLowerCase().includes(lowerQuery) ||
                    p.brand?.toLowerCase().includes(lowerQuery) ||
                    p.barcode?.includes(query)
                )
            }

            // Apply region filter
            if (selectedRegion) {
                filtered = filtered.filter(p => p.region === selectedRegion)
            }

            // Apply brand filter
            if (selectedBrand) {
                filtered = filtered.filter(p =>
                    p.brand?.toLowerCase().includes(selectedBrand.toLowerCase())
                )
            }

            setFilteredProducts(filtered)
        }
    }, [query, products, selectedRegion, selectedBrand])

    const fetchProducts = async () => {
        setLoading(true)
        try {
            // Fetch from products endpoint
            console.log('Fetching from /products endpoint...')
            let url = 'http://localhost:8000/products?limit=200'

            const res = await fetch(url)
            console.log('Response status:', res.status)

            if (res.ok) {
                const data: ProductsResponse = await res.json()
                console.log('Received data:', data)
                console.log(`Found ${data.products?.length || 0} products`)

                if (data.products && data.products.length > 0) {
                    setProducts(data.products)
                    setFilteredProducts(data.products)
                    setTotal(data.total || 0)

                    // Extract unique regions and brands from the data
                    const uniqueRegions = [...new Set(data.products.map(p => p.region).filter(Boolean))] as string[]
                    const uniqueBrands = [...new Set(data.products.map(p => p.brand).filter(Boolean))] as string[]
                    setRegions(uniqueRegions)
                    setBrands(uniqueBrands)

                    console.log('Products loaded successfully!')
                } else {
                    console.log('No products found')
                    setProducts([])
                    setFilteredProducts([])
                    setTotal(0)
                }
            } else {
                console.error('Failed to fetch from /products:', res.statusText)
                setProducts([])
                setFilteredProducts([])
                setTotal(0)
            }
        } catch (e) {
            console.error('Error fetching products:', e)
            setProducts([])
            setFilteredProducts([])
            setTotal(0)
        } finally {
            setLoading(false)
        }
    }

    const clearFilters = () => {
        setSelectedRegion('')
        setSelectedBrand('')
        setQuery('')
    }

    const hasActiveFilters = selectedRegion || selectedBrand || query

    return (
        <>
            <Head>
                <title>Products - EatSmart</title>
                <meta name="description" content="Browse our curated list of India-friendly packaged products with nutrition details" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
            </Head>

            <main className={styles.productsMain}>
                {/* Hero Section */}
                <section className={styles.productsHero}>
                    <div className={styles.heroContent}>
                        <h1 className={styles.heroTitle}>
                            Discover Healthy Products
                        </h1>
                        <p className={styles.heroSubtitle}>
                            Browse through our curated collection of {total} verified food products from across India
                        </p>

                        {/* Search Bar */}
                        <form className={styles.searchForm} onSubmit={(e) => e.preventDefault()} role="search">
                            <div className={styles.searchWrapper}>
                                <svg className={styles.searchIcon} width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
                                    <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                </svg>
                                <input
                                    className={styles.searchInput}
                                    placeholder="Search by product name, brand, or barcode..."
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    aria-label="Search products"
                                />
                                {query && (
                                    <button
                                        type="button"
                                        className={styles.clearSearchBtn}
                                        onClick={() => setQuery('')}
                                        aria-label="Clear search"
                                    >
                                        ×
                                    </button>
                                )}
                            </div>
                        </form>
                    </div>
                </section>

                {/* Filters Section */}
                <section className={styles.filtersSection}>
                    <div className={styles.filtersContainer}>
                        <div className={styles.filtersHeader}>
                            <h2 className={styles.filtersTitle}>Filter Products</h2>
                            {hasActiveFilters && (
                                <button
                                    className={styles.clearFiltersBtn}
                                    onClick={clearFilters}
                                >
                                    Clear All Filters
                                </button>
                            )}
                        </div>

                        <div className={styles.filterControls}>
                            {/* Region Filter */}
                            <div className={styles.filterGroup}>
                                <label htmlFor="region-filter" className={styles.filterLabel}>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <circle cx="12" cy="9" r="2.5" stroke="currentColor" strokeWidth="2" />
                                    </svg>
                                    Region
                                </label>
                                <select
                                    id="region-filter"
                                    className={styles.filterSelect}
                                    value={selectedRegion}
                                    onChange={(e) => setSelectedRegion(e.target.value)}
                                >
                                    <option value="">All Regions</option>
                                    {regions.map(region => (
                                        <option key={region} value={region}>{region}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Brand Filter */}
                            <div className={styles.filterGroup}>
                                <label htmlFor="brand-filter" className={styles.filterLabel}>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M20 7h-4V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    Brand
                                </label>
                                <select
                                    id="brand-filter"
                                    className={styles.filterSelect}
                                    value={selectedBrand}
                                    onChange={(e) => setSelectedBrand(e.target.value)}
                                >
                                    <option value="">All Brands</option>
                                    {brands.slice(0, 50).map(brand => (
                                        <option key={brand} value={brand}>{brand}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Results Count */}
                        <div className={styles.resultsInfo}>
                            Showing <strong>{filteredProducts.length}</strong> {filteredProducts.length === 1 ? 'product' : 'products'}
                            {hasActiveFilters && <> matching your filters</>}
                        </div>
                    </div>
                </section>

                {/* Products Grid */}
                <section className={styles.productsSection}>
                    <div className={styles.productsContainer}>
                        {loading ? (
                            <div className={styles.loadingState}>
                                <div className={styles.spinner}></div>
                                <p>Loading delicious products...</p>
                            </div>
                        ) : filteredProducts.length === 0 ? (
                            <div className={styles.emptyState}>
                                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="12" cy="12" r="10" stroke="#E53A33" strokeWidth="2" opacity="0.3" />
                                    <path d="M12 8v4M12 16h.01" stroke="#E53A33" strokeWidth="2" strokeLinecap="round" />
                                </svg>
                                <h3>No products found</h3>
                                <p>Try adjusting your filters or search query</p>
                                {hasActiveFilters && (
                                    <button className={styles.clearFiltersBtn} onClick={clearFilters}>
                                        Clear All Filters
                                    </button>
                                )}
                            </div>
                        ) : (
                            <div className={styles.productsGrid}>
                                {filteredProducts.map((product) => (
                                    <ProductCard key={product.id} {...product} />
                                ))}
                            </div>
                        )}
                    </div>
                </section>
            </main>
        </>
    )
}
