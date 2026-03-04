import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from "react";

type HeaderScrollContextValue = {
  headerHidden: boolean;
  setHeaderHidden: (hidden: boolean) => void;
  /** Ref to the outer scroll container (home mobile). Header scrolls this to top when blank area is tapped. */
  scrollContainerRef: React.MutableRefObject<HTMLDivElement | null>;
};

const HeaderScrollContext = createContext<HeaderScrollContextValue | null>(null);

export function HeaderScrollProvider({ children }: { children: ReactNode }) {
  const [headerHidden, setHeaderHidden] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const stableSet = useCallback((hidden: boolean) => setHeaderHidden(hidden), []);
  const value = {
    headerHidden,
    setHeaderHidden: stableSet,
    scrollContainerRef,
  };
  return (
    <HeaderScrollContext.Provider value={value}>
      {children}
    </HeaderScrollContext.Provider>
  );
}

export function useHeaderScroll() {
  const ctx = useContext(HeaderScrollContext);
  if (!ctx)
    return {
      headerHidden: false,
      setHeaderHidden: () => {},
      scrollContainerRef: { current: null } as React.MutableRefObject<HTMLDivElement | null>,
    };
  return ctx;
}
