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
        <div className="flex items-center">
            <input
                type="text"
                placeholder="Search"
                value={searchTerm}
                onChange={handleChange}
                className="bg-gray-200 focus:bg-white focus:outline-none border border-gray-300 rounded-l px-4 py-2"
            />
            <button
                type="button"
                className="bg-blue-500 hover:bg-blue-600 text-white rounded-r px-4 py-2"
                onClick={handleSearch}
            >
                Search
            </button>
        </div>
    );
};

export default SearchInput;
