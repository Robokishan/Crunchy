import React, { useCallback, useEffect, useState } from 'react';

interface SearchInputProps {
    onSearch: (searchTerm: string) => void;
}

const SearchInput: React.FC<SearchInputProps> = ({ onSearch }) => {
    const [searchTerm, setSearchTerm] = useState<string>('');

    const handleSearch = useCallback(() => {
        onSearch(searchTerm);
    }, [onSearch, searchTerm]);

    useEffect(() => {
        const delayDebounceFn = setTimeout(() => {
            handleSearch();
        }, 500);

        return () => {
            clearTimeout(delayDebounceFn);
        };
    }, [handleSearch, searchTerm]);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(event.target.value);
    };

    return (
        <div className="flex">
            <input
                type="search"
                placeholder="Search"
                value={searchTerm}
                onChange={handleChange}
                className="input-base rounded-r-none border-r-0"
                aria-label="Search"
            />
            <button
                type="button"
                className="rounded-r-input bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:bg-brand-500 dark:hover:bg-brand-600"
                onClick={handleSearch}
            >
                Search
            </button>
        </div>
    );
};

export default SearchInput;
