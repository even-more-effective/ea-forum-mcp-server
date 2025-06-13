from typing import TypedDict, List, Optional, Union


class Tag(TypedDict):
    _id: str
    name: str
    slug: str


class AlgoliaSearchHit(TypedDict):
    objectID: str
    userId: str
    url: Optional[str]
    title: str
    slug: str
    baseScore: int
    curated: bool
    commentCount: int
    postedAt: str
    createdAt: str
    publicDateMs: int
    isEvent: bool
    lastCommentedAt: str
    af: bool
    tags: List[Tag]
    authorSlug: str
    authorDisplayName: str
    authorFullName: Optional[str]
    feedName: Optional[str]
    feedLink: Optional[str]
    body: str
    _id: str
    _index: str


class AlgoliaSearchResult(TypedDict):
    hits: List[AlgoliaSearchHit]
    nbHits: int
    page: int
    nbPages: int
    hitsPerPage: int
    exhaustiveNbHits: bool
    exhaustiveType: bool
    exhaustive: dict
    query: str
    params: str
    index: str
    processingTimeMS: int


class PostContents(TypedDict):
    html: str
    plaintextDescription: str
    wordCount: int


class User(TypedDict):
    _id: str
    displayName: str
    slug: str
    karma: int


class PostContent(TypedDict):
    _id: str
    title: str
    slug: str
    baseScore: int
    voteCount: int
    postedAt: str
    createdAt: Optional[str]
    url: Optional[str]
    contents: PostContents
    user: User
    tags: List[Tag]
    commentCount: int
    lastCommentedAt: str


class GraphQLPostResponse(TypedDict):
    data: dict


class SearchOptions(TypedDict):
    emptyStringSearchResults: str


class SearchParams(TypedDict):
    hitsPerPage: int
    query: str
    numericFilters: List[str]
    tagFilters: str
    page: Optional[int]
    facetFilters: Optional[List[List[str]]]
    highlightPreTag: Optional[str]
    highlightPostTag: Optional[str]


class SearchQuery(TypedDict):
    indexName: str
    params: SearchParams


class AlgoliaSearchRequest(TypedDict):
    options: SearchOptions
    queries: List[SearchQuery]